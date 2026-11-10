import casino
import karma
import karma_dialogue
from utils import advance_time, _get_wonderland_max_floor
from inventory import add_item_to_inventory
from resources.items import random_equipment, build_item, ITEM_RARITY, market_value, market_anchor_level
from city_dialogue import service_dialogue
from gui.terminal import term
import random


# ── Capture Net tier definitions ─────────────────────────────────────────────
# (item_id, display_name, cost, per_tier_cap, unlock_floor, rarity_mult_bonus)
_NET_TIERS = [
    ("capture_net",             "Capture Net",              550,  10,  1,  25),
    ("reinforced_capture_net",  "Reinforced Capture Net",  1200,   5, 20,  37),
    ("mythril_capture_net",     "Mythril Capture Net",     3000,   3, 40,  55),
]


def _karma_price(player, cost):
    """Black Market inverse Karma + the title discount."""
    discount = 0.0
    if karma.is_enabled(player):
        discount = min(20, max(0, -karma.get_karma(player) * 0.2))
    from titles import mod as _title_mod
    title_discount = min(10, max(0, _title_mod(player, "black_market_pct") * 100))
    discount = min(30, discount + title_discount)
    if discount <= 0:
        return cost
    return max(1, int(round(cost * (1 - discount / 100.0))))


def _outlaw_stock_available(player, city_id):
    """Outlaw-only stock at Karma ≤ −25; Wonderland waits for its own pass."""
    return (
        city_id != "wonderland"
        and karma.is_enabled(player)
        and karma.get_karma(player) <= -25
    )


def _buy_capture_nets(player, city_id):
    """Sub-menu for purchasing tiered capture nets from the Black Market.

    Each tier has its own purchase cap (enforced per-tier, not global).
    Tiers unlock based on the player's maximum dungeon floor reached.
    """
    # Determine player's overall max floor across all cities
    city_floors = player.get("city_floors", {})
    max_floor = max((p.get("max_floor", 1) for p in city_floors.values()), default=1)

    # Build net counts from inventory
    net_counts = {}
    for item in player.get("inventory", []):
        if item.get("capture_net"):
            net_id = item.get("id", "capture_net")
            net_counts[net_id] = net_counts.get(net_id, 0) + item.get("count", 1)

    while True:
        term.clear()
        term.print("The dealer spreads a selection of nets across the counter.\n")

        sub_options = []
        available_tiers = []

        for net_id, name, base_cost, cap, unlock_floor, bonus in _NET_TIERS:
            cost = _karma_price(player, base_cost)
            owned = net_counts.get(net_id, 0)
            unlocked = max_floor >= unlock_floor
            if unlocked:
                if owned >= cap:
                    sub_options.append(f"{name} — SOLD OUT ({owned}/{cap} owned)")
                else:
                    sub_options.append(f"{name} — {cost} gold (+{bonus} catch) [{owned}/{cap}]")
                available_tiers.append((net_id, name, cost, cap, bonus, owned))
            else:
                sub_options.append(f"??? — Unlocks at Floor {unlock_floor}")

        sub_options.append("Back")

        choice = term.menu(sub_options, prompt="Pick a net to purchase:")

        if choice < 0 or choice >= len(available_tiers):
            return  # Back or invalid

        net_id, name, cost, cap, bonus, owned = available_tiers[choice]

        if owned >= cap:
            term.print("The dealer shakes their head. 'You've cleaned me out of those already.'")
            term.pause()
            continue

        if player.get("gold", 0) < cost:
            term.print("Not enough gold.")
            term.pause()
            continue

        # Confirm purchase
        if not term.confirm(f"Buy {name} for {cost} gold? (+{bonus} catch bonus)"):
            continue

        player["gold"] -= cost
        net = build_item(net_id, rarity="common")
        if add_item_to_inventory(player, net):
            net_counts[net_id] = net_counts.get(net_id, 0) + 1
            term.print(f"You acquire: {net['name']} (+{bonus} catch bonus)")
            service_dialogue(city_id, "black_market", "buy")
        else:
            term.print("Your bag is full! Cannot carry the net.")
            player["gold"] += cost  # refund
        term.pause()


def _woodcutter_interaction(player):
    """Handle the Woodcutter encounter in Wonderland's Black Market.

    Phase 1: Give Woodcutter's Broken Axe (requires floor 15+ — Red Hood
             arrives after Floor 10 and her Wolf chapter ends at 20)
    Phase 2: Upgrade Broken Axe → Grandmother's Axe (requires Big Bad Wolf defeat + materials)
    """
    from resources.dialogues.wonderland import WONDERLAND_WOODCUTTER_DIALOGUE as WD
    from combat.ally import get_heroine_in_party

    term.clear()

    # ── Already upgraded ────────────────────────────────────────────────
    if player.get("wl_woodcutter_axe_upgraded"):
        for line in WD.get("upgrade_already", [WD["leave"][0]]):
            term.print(line)
        term.pause()
        return

    woodcutter_spoken = player.get("wl_woodcutter_spoken", False)
    wolf_defeated = player.get("wl_boss_defeated_big_bad_wolf", False)

    # ── Phase 2: Upgrade check ──────────────────────────────────────────
    if woodcutter_spoken and wolf_defeated:
        red_hood = get_heroine_in_party(player, "red_hood")
        has_axe_equipped = (
            red_hood and
            red_hood.get("equipped", {}).get("weapon", {}).get("id") == "woodcutters_broken_axe"
        )

        has_tooth = any(
            item.get("id") == "wolfs_tooth"
            for item in player.get("inventory", [])
        )
        has_scrap = any(
            item.get("id") == "crimson_hood_scrap"
            for item in player.get("inventory", [])
        )

        if not has_axe_equipped:
            for line in WD.get("upgrade_no_red_hood", [WD["leave"][0]]):
                term.print(line)
            term.pause()
            return

        if not (has_tooth and has_scrap):
            for line in WD.get("upgrade_no_materials", [WD["leave"][0]]):
                term.print(line)
            term.pause()
            return

        # ── Perform upgrade ──────────────────────────────────────────
        for line in WD.get("upgrade_intro", []):
            term.print(line)
        term.print("")
        choice = term.menu([
            "Yes — reforge Grandmother's Axe!",
            "Not yet.",
        ], prompt="")
        if choice != 0:
            term.print(WD.get("leave", [""])[0])
            term.pause()
            return

        for line in WD.get("upgrade_perform", []):
            term.print(line)

        # Remove materials from inventory
        for mat_id in ("wolfs_tooth", "crimson_hood_scrap"):
            for item in list(player.get("inventory", [])):
                if item.get("id") == mat_id:
                    player["inventory"].remove(item)
                    break

        # Upgrade Red Hood's equipped weapon
        axe = build_item("grandmothers_axe", rarity="unique", enhance=5)
        red_hood["equipped"]["weapon"] = axe

        from combat.elemental import compute_ally_elemental
        e_res, e_dmg = compute_ally_elemental(red_hood)
        red_hood["elemental_res"] = e_res
        red_hood["elemental_dmg"] = e_dmg

        from combat.ally_skills import swap_redhood_to_vorpal_skills, grant_redhood_upgrade_skill
        swap_redhood_to_vorpal_skills(red_hood)
        grant_redhood_upgrade_skill(red_hood)

        player["wl_woodcutter_axe_upgraded"] = True

        term.print("")
        term.print("🪓 Grandmother's Axe is whole! Red Hood gains 'Through the Forest'!")
        term.pause()
        return

    # ── Phase 1: First meeting ──────────────────────────────────────────
    if not woodcutter_spoken:
        for line in WD.get("enter", []):
            term.print(line)
        term.print("")

        choice = term.menu([
            '"You knew the Wolf would come back?"',
            '"Who are you, really?"',
            '"What do you have for me?"',
        ], prompt="")
        if choice < 0:
            term.print(WD.get("leave", [""])[0])
            term.pause()
            return

        for line in WD.get("axe_gift", []):
            term.print(line)
        term.print("")

        axe = build_item("woodcutters_broken_axe", rarity="unique", enhance=0)
        if not add_item_to_inventory(player, axe):
            term.print("\nYour inventory is full! Make room and return.")
            term.pause()
            return

        player["wl_woodcutter_spoken"] = True
        term.print("\n🪓 Received: Woodcutter's Broken Axe")
        term.pause()
        return

    # ── Already spoken, not yet upgrade time ────────────────────────────
    for line in WD.get("axe_already", [WD["leave"][0]]):
        term.print(line)
    term.pause()


def black_market_service(player, city_id):
    """Black market: buy rare/illegal items at high prices."""
    service_dialogue(city_id, "black_market", "enter")
    market_line = karma_dialogue.service_line(player, "black_market", city_id)
    if market_line:
        term.print(f'  "{market_line}"')
    term.print("A shadowy figure whispers about forbidden wares.")

    # ── Wonderland Woodcutter check (Floor 15+; Red Hood joins at 11 and
    #    her Wolf chapter ends at 20) ───────────────────────────────────
    woodcutter_available = (
        city_id == "wonderland" and
        _get_wonderland_max_floor(player) >= 15
    )

    options = [
        "Buy mysterious relic (450 gold) – random rare item",
        "Buy Capture Nets...",
    ]
    outlaw_available = _outlaw_stock_available(player, city_id)
    if outlaw_available:
        term.print("A sealed crate sits under the counter, reserved for outlaws.")
        options.append("Buy sealed outlaw crate — epic relic")

    # ── Veilholt: Looking Glass Shard (when floor milestone met) ────────
    _looking_glass_available = False
    if city_id == "veilholt" and not player.get("wonderland_unlocked"):
        # Two different biomes at Floor 20+ — same-biome cities share one
        # dungeon depth, so city records are not a valid count any more.
        from leveling import get_biomes_cleared_to_cap
        biomes_f20 = get_biomes_cleared_to_cap(player, 20)
        has_shard = any(
            item.get("id") == "looking_glass_shard"
            for item in player.get("inventory", [])
        )
        if len(biomes_f20) >= 2 and not has_shard:
            _looking_glass_available = True
            options.append("Buy Looking Glass Shard - 5,000 gold")

    if woodcutter_available:
        options.append("Speak with the Woodcutter")

    # ── The back room (casino games) ────────────────────────────────────
    back_room_available = city_id != "wonderland"
    if back_room_available:
        options.append(casino.back_room_entry_label(player))

    options.append("Leave")

    choice = term.menu(options, prompt="Available goods:")

    # Track option indices dynamically
    opt_idx = 0
    relic_opt = opt_idx; opt_idx += 1          # 0
    net_opt = opt_idx; opt_idx += 1            # 1
    outlaw_opt = opt_idx if outlaw_available else -1
    if outlaw_available: opt_idx += 1
    glass_opt = opt_idx if _looking_glass_available else -1
    if _looking_glass_available: opt_idx += 1  # next (if available)
    woodcutter_opt = opt_idx if woodcutter_available else -1
    if woodcutter_available: opt_idx += 1
    back_room_opt = opt_idx if back_room_available else -1
    if back_room_available: opt_idx += 1
    leave_opt = opt_idx                         # last

    if choice == relic_opt:
        # Relic pricing follows computed item value (economy tuning)
        relic_rarity = random.choices(
            ["common", "uncommon", "rare", "epic", "legendary"],
            weights=[10, 22, 30, 24, 14])[0]
        item = random_equipment(rarity=relic_rarity)
        anchor = market_anchor_level(player)
        cost = max(1, int(round(450 * market_value(item, anchor) / 4)))
        cost = _karma_price(player, cost)
        if player.get("gold", 0) >= cost:
            player["gold"] -= cost
            if add_item_to_inventory(player, item):
                term.print(f"You acquire: {item['name']} ({item['rarity'].title()})")
                service_dialogue(city_id, "black_market", "buy")
            else:
                term.print("Your bag is full! Cannot carry the relic.")
                player["gold"] += cost  # refund
        else:
            term.print(f"Not enough gold. This relic costs {cost:,}g.")

    elif choice == net_opt:
        _buy_capture_nets(player, city_id)

    elif outlaw_available and choice == outlaw_opt:
        item = random_equipment(rarity="epic")
        anchor = market_anchor_level(player)
        cost = max(1, int(round(900 * market_value(item, anchor) / 4)))
        cost = _karma_price(player, cost)
        if player.get("gold", 0) >= cost:
            player["gold"] -= cost
            if add_item_to_inventory(player, item):
                term.print(f"The dealer unlocks a sealed crate. You acquire: {item['name']} (Epic, outlaw stock)")
                service_dialogue(city_id, "black_market", "buy")
            else:
                term.print("Your bag is full! Cannot carry the crate's contents.")
                player["gold"] += cost  # refund
        else:
            term.print(f"Not enough gold. The outlaw crate costs {cost:,}g.")

    elif choice == glass_opt:
        # Looking Glass Shard — key item for Wonderland unlock
        cost = 5000
        if player.get("gold", 0) >= cost:
            term.print(
                "The dealer produces a shard of glass that reflects nothing "
                "from this world."
            )
            term.print(
                "'This? Found it in the forest. Shows things that aren't... "
                "yet. 5,000 gold.'"
            )
            if term.confirm("Buy it?"):
                player["gold"] -= cost
                shard = build_item("looking_glass_shard")
                if add_item_to_inventory(player, shard):
                    term.print(
                        "\nThe shard is cold in your palm. For a moment, you see "
                        "a sky the colour of aged parchment reflected in its surface."
                    )
                    term.print("You acquired the Looking Glass Shard!")
                else:
                    term.print("Your bag is full!")
                    player["gold"] += cost
        else:
            term.print("Not enough gold. You need 5,000 gold.")

    elif choice == woodcutter_opt:
        _woodcutter_interaction(player)

    elif back_room_available and choice == back_room_opt:
        status = casino.back_room_status(player)
        if not status.get("ok"):
            from facilities.casino_ui import print_back_room_refusal
            print_back_room_refusal(player, status)
            term.pause()
            advance_time(player, 30)
            return
        from facilities.casino_ui import back_room_menu
        back_room_menu(player, city_id)
        term.pause()
        # The back-room sub-menu charges 20 minutes per hand; skip the
        # normal 30-minute Black Market visit fee to avoid double-charging.
        return

    elif choice == leave_opt or choice == -1:
        service_dialogue(city_id, "black_market", "leave")
        term.pause()
        return

    term.pause()
    advance_time(player, 30)