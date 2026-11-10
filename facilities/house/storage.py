"""facilities/house/storage.py — the house storage chest.

Moves items between the player's bag and the house chest, respecting the
equipment/other bag caps and the tier-based chest capacity. Wedding
accessories are soulbound and cannot be deposited.
"""

from inventory import (
    count_inventory,
    get_inventory_caps,
    get_sorted_equipment,
    get_sorted_items,
)
from gui.terminal import term

from .core import _house_level_data


def _house_storage(player, city_id, house):
    """Move items between inventory and house storage chest."""
    lvl_data = _house_level_data(house)
    cap      = lvl_data["storage_cap"]
    storage  = house["storage"]

    while True:
        term.clear()
        inv     = player.get("inventory", [])
        equip_cap, other_cap = get_inventory_caps(player)
        equip_count, other_count = count_inventory(player)
        term.print(f"=== House Storage ({len(storage)}/{cap} slots used) ===")
        term.print(f"Your Bag: {equip_count}/{equip_cap} equipment | {other_count}/{other_cap} items")

        term.print("\n-- Chest --")
        if storage:
            for i, itm in enumerate(storage):
                term.print(f"  {i+1}. {itm['name']} ({itm['type']})")
        else:
            term.print("  (empty)")

        term.print("\n-- Your Bag --")
        if inv:
            sorted_equip = get_sorted_equipment(player)
            sorted_items = get_sorted_items(player)
            all_sorted = sorted_equip + sorted_items
            for i, itm in enumerate(all_sorted):
                if itm.get("type") == "equipment":
                    tag = f"[{itm.get('rarity','common')}]"
                    term.print(f"  {i+1}. {itm['name']} ({itm['slot']}) {tag}")
                else:
                    term.print(f"  {i+1}. {itm['name']} ({itm['type']})")
        else:
            term.print("  (empty)")

        act_idx = term.menu(["Deposit to chest", "Withdraw from chest", "Back"], prompt="Storage action:")
        if act_idx == 0:
            act = "d"
        elif act_idx == 1:
            act = "w"
        else:
            act = "b"

        if act == "d":
            if not inv:
                term.print("Your bag is empty.")
                term.pause()
                continue
            if len(storage) >= cap:
                term.print(f"Chest is full ({cap} slots).")
                term.pause()
                continue
            term.print("\nEnter numbers to deposit (e.g. '1 3 5', '1-4', or 'all'). 0 to cancel.")
            raw = term.input("Deposit which items? ").strip().lower()
            if raw in ("", "0", "cancel"):
                term.print("Cancelled.")
                term.pause()
                continue

            sorted_equip = get_sorted_equipment(player)
            sorted_items = get_sorted_items(player)
            all_sorted = sorted_equip + sorted_items
            indices = set()
            if raw == "all":
                indices = set(range(len(all_sorted)))
            else:
                for part in raw.split():
                    if "-" in part:
                        try:
                            a, b = part.split("-", 1)
                            indices.update(range(int(a) - 1, int(b)))
                        except ValueError:
                            pass
                    else:
                        try:
                            indices.add(int(part) - 1)
                        except ValueError:
                            pass

            indices = sorted([i for i in indices if 0 <= i < len(all_sorted)], reverse=True)
            if not indices:
                term.print("No valid items selected.")
                term.pause()
                continue

            # Check capacity before depositing
            from combat.weapon.wedding_specials import is_wedding_item_soulbound
            filtered_indices = []
            for i in indices:
                item = all_sorted[i]
                if is_wedding_item_soulbound(item):
                    term.print(f"  {item['name']} is soulbound — it cannot leave your side.")
                else:
                    filtered_indices.append(i)

            if not filtered_indices:
                term.print("No valid items to deposit (all selected items are soulbound).")
                term.pause()
                continue

            deposit_count = len(filtered_indices)
            if len(storage) + deposit_count > cap:
                term.print(f"Not enough chest space. Can only store {cap - len(storage)} more items.")
                term.pause()
                continue

            for i in filtered_indices:
                item = all_sorted[i]
                orig_idx = next(idx for idx, itm in enumerate(player["inventory"]) if itm is item)
                player["inventory"].pop(orig_idx)
                storage.append(item)
            term.print(f"Stored {deposit_count} item(s) in your chest.")
            term.pause()

        elif act == "w":
            if not storage:
                term.print("The chest is empty.")
                term.pause()
                continue
            term.print("\nEnter numbers to withdraw (e.g. '1 3 5', '1-4', or 'all'). 0 to cancel.")
            raw = term.input("Withdraw which items? ").strip().lower()
            if raw in ("", "0", "cancel"):
                term.print("Cancelled.")
                term.pause()
                continue

            indices = set()
            if raw == "all":
                indices = set(range(len(storage)))
            else:
                for part in raw.split():
                    if "-" in part:
                        try:
                            a, b = part.split("-", 1)
                            indices.update(range(int(a) - 1, int(b)))
                        except ValueError:
                            pass
                    else:
                        try:
                            indices.add(int(part) - 1)
                        except ValueError:
                            pass

            indices = sorted([i for i in indices if 0 <= i < len(storage)], reverse=True)
            if not indices:
                term.print("No valid items selected.")
                term.pause()
                continue

            # Check bag capacity before withdrawing
            withdraw_equip = sum(1 for i in indices if storage[i].get("type") == "equipment")
            withdraw_other = len(indices) - withdraw_equip
            equip_cap, other_cap = get_inventory_caps(player)
            equip_count, other_count = count_inventory(player)
            if equip_count + withdraw_equip > equip_cap:
                term.print(f"Not enough equipment bag space. Can hold {equip_cap - equip_count} more equipment.")
                term.pause()
                continue
            if other_count + withdraw_other > other_cap:
                term.print(f"Not enough item bag space. Can hold {other_cap - other_count} more items.")
                term.pause()
                continue

            for i in indices:
                item = storage.pop(i)
                player.setdefault("inventory", []).append(item)
            term.print(f"Took {len(indices)} item(s) from the chest.")
            term.pause()

        elif act == "b":
            break
