from inventory import (get_inventory_caps, count_inventory, get_sorted_equipment, get_sorted_items,
                       add_item_to_inventory, remove_item_by_reference)

# ── GUI terminal detection (safe import for terminal mode) ──────────
try:
    from gui.terminal import get_terminal as _get_gui_terminal
except ImportError:
    _get_gui_terminal = lambda: None


def _term():
    """Return the GUI Terminal if running in GUI mode, else None."""
    return _get_gui_terminal()


def _tprint(*args, sep=" "):
    """Print to GUI if available, else to terminal."""
    t = _term()
    text = sep.join(str(a) for a in args)
    if t:
        t.print(text)
    else:
        print(text)


def _tpause(prompt="Press Enter to continue..."):
    """Pause for user acknowledgement."""
    t = _term()
    if t:
        t.pause(prompt)
    else:
        input(prompt)


def _tclear():
    """Clear screen (no-op in GUI since output is managed by the panel)."""
    t = _term()
    if t:
        t.clear()
    else:
        from utils import clear_screen
        clear_screen()


def _tmenu(options, prompt="Choose an option:", allow_cancel=False, cancel_label="Cancel"):
    """Show a menu; returns 0-based index or -1."""
    t = _term()
    if t:
        return t.menu(options, prompt=prompt, allow_cancel=allow_cancel, cancel_label=cancel_label)
    else:
        for i, opt in enumerate(options):
            print(f"{i+1}. {opt}")
        if allow_cancel:
            print(f"0. {cancel_label}")
        try:
            choice = input(prompt + " ").strip()
            idx = int(choice) - 1
            if allow_cancel and idx == -1:
                return -1
            if 0 <= idx < len(options):
                return idx
        except (ValueError, IndexError):
            pass
        return -1


def _tinput(prompt=""):
    """Free-text input. Falls back to terminal input() if no GUI."""
    t = _term()
    if t:
        return t.input(prompt)
    else:
        return input(prompt)


def _format_equipment_stat_line(item):
    """Format equipment mods for inventory display."""
    if item.get("type") != "equipment":
        return ""
    slot = item.get("slot", "?").title()
    mods = item.get("mods", {})
    mod_s = ", ".join(
        f"{stat[:3]} {'+' if v >= 0 else ''}{v}"
        for stat, v in mods.items()
    )
    return f"[{slot}{(' | ' + mod_s) if mod_s else ''}]"


def prompt_acquire_item(player, item):
    """Try to add item to inventory. If full, prompt player to discard an existing item or drop the new one.
    Returns True if the item ends up in inventory, False if it was dropped.
    """
    if add_item_to_inventory(player, item):
        return True

    equip_cap, other_cap = get_inventory_caps(player)
    equip_count, other_count = count_inventory(player)

    is_equip = item.get("type") == "equipment"
    cat_name = "Equipment" if is_equip else "Items"
    cur_count = equip_count if is_equip else other_count
    cur_cap = equip_cap if is_equip else other_cap

    _tprint(f"\n⚠️  Your {cat_name.lower()} bag is full! ({cur_count}/{cur_cap})")

    if is_equip:
        candidates = get_sorted_equipment(player)
        header = "-- Equipment --"
    else:
        candidates = get_sorted_items(player)
        header = "-- Items --"

    # Filter out unique items — they cannot be discarded
    candidates = [itm for itm in candidates if not itm.get("unique")]

    if not candidates:
        _tprint(f"You have no {cat_name.lower()} to discard. The item is dropped.")
        return False

    _tprint(f"\n{header}")
    for idx, itm in enumerate(candidates):
        extra = f" ({itm['slot']})" if is_equip else f" ({itm['type']})"
        count_str = f" (x{itm.get('count', 1)})" if not is_equip and itm.get('count', 1) > 1 else ""
        stat = _format_equipment_stat_line(itm) if is_equip else ""
        stat_part = f" {stat}" if stat else ""
        _tprint(f"  {idx+1}. {itm['name']}{count_str}{extra}{stat_part} [{itm.get('rarity','common')}]")

    _tprint(f"\n[D]rop the new item  or  enter a number (1-{len(candidates)}) to discard that item instead.")
    choice = _tinput("Choice: ").strip().lower()

    if choice == "d":
        _tprint(f"You drop the {item['name']}.")
        return False

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(candidates):
            discarded = candidates[idx]
            remove_item_by_reference(player, discarded)
            player.setdefault("inventory", []).append(item)
            _tprint(f"Discarded {discarded['name']}. Acquired {item['name']}!")
            return True
        else:
            _tprint("Invalid choice. Dropping the new item.")
            return False
    except (ValueError, StopIteration):
        _tprint("Invalid choice. Dropping the new item.")
        return False
