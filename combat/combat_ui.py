# combat_ui.py – HUD and status formatting
from utils import clear_screen, format_time
from combat.status_effects import format_player_status_line
from combat.action_menu import get_action_menu
from combat.abyss_fang import is_abyssal_tempo_active, get_abyss_fang_cooldown_display
from combat.captain_cutlass import get_captain_cutlass_cooldown_display
from combat.ally import format_ally_status_line, _ally_action_menu
from combat.ally_skills import get_all_ally_skills
from combat.skills import get_all_unlocked_skills


def format_enemy_status_line(enemy, extra=""):
    statuses = []
    if enemy.get("slowed"):
        statuses.append("Slowed")
    if enemy.get("stunned"):
        statuses.append("Stunned")
    if enemy.get("blinded"):
        statuses.append("Blinded")
    if enemy.get("frozen"):
        statuses.append("Frozen")
    if any(d["type"] == "burn" for d in enemy.get("active_debuffs", [])):
        statuses.append("Burning")
    if enemy.get("expose_stacks", 0) > 0:
        statuses.append(f"Exposed×{enemy['expose_stacks']}")
    status_str = f" ({', '.join(statuses)})" if statuses else ""
    return f"{enemy['name']} - HP: {enemy['hp']}{status_str}{extra}"


def print_pre_initiative_enemies(enemies):
    """Print a simple enemy list before initiative is rolled."""
    print("ENEMIES:")
    for idx, e in enumerate(enemies):
        mg_symbol = "♀" if e.get("monster_girl") else ""
        print(f"  [{idx+1}] {e['name']} ({e['hp']}/{e['max_hp']}) {mg_symbol}")


def _hp_bar(current, max_hp, width=12):
    """Return a simple ASCII HP bar."""
    if max_hp <= 0:
        return "[            ]"
    ratio = current / max_hp
    filled = int(ratio * width)
    filled = max(0, min(width, filled))
    empty = width - filled
    bar = "#" * filled + "." * empty
    return f"[{bar}]"


def _center_text(text, width):
    """Center text within a given width, truncating if necessary."""
    if len(text) >= width:
        return text[:width]
    pad = width - len(text)
    left = pad // 2
    right = pad - left
    return " " * left + text + " " * right


def _get_entity_buff_tags(entity):
    """Return a short buff/debuff tag string for any entity (player, ally, enemy)."""
    statuses = []
    # Flag-based debuffs
    if entity.get("stunned"):
        statuses.append("STN")
    if entity.get("slowed"):
        statuses.append("SLW")
    if entity.get("blinded"):
        statuses.append("BLD")
    if entity.get("frozen"):
        statuses.append("FRZ")
    if entity.get("silenced"):
        statuses.append("SIL")
    if entity.get("dreaded"):
        statuses.append("DRD")
    if entity.get("cursed"):
        statuses.append("CRS")
    if entity.get("hunters_mark"):
        statuses.append("MRK")

    # Debuff types from active_debuffs
    debuff_map = {
        "poison": "PSN",
        "bleed": "BLE",
        "burn": "BRN",
        "slow": "SLW",
        "weaken": "WKN",
        "silence": "SIL",
        "dread": "DRD",
        "blind": "BLD",
        "curse": "CRS",
        "fear": "FER",
        "vulnerable": "VUL",
    }
    for d in entity.get("active_debuffs", []):
        tag = debuff_map.get(d["type"])
        if tag and tag not in statuses:
            statuses.append(tag)

    # Expose stacks (enemy only)
    expose = entity.get("expose_stacks", 0)
    if expose > 0:
        statuses.append(f"EXP×{expose}")

    # Buffs from active_buffs
    for b in entity.get("active_buffs", []):
        btype = b.get("type")
        if btype == "hot":
            tag = "REG"
        elif btype == "defense":
            tag = "DEF"
        elif btype == "blessing":
            tag = "BLS"
        elif btype == "well_rested":
            tag = "RST"
        elif b.get("stat"):
            stat = b["stat"]
            if stat == "all":
                tag = "ALL+"
            else:
                tag = f"+{stat[:3].upper()}"
        else:
            continue
        if tag not in statuses:
            statuses.append(tag)

    # Elemental tag: show dominant element if dmg > 1.1 for player/ally, or highest res for enemy
    e_dmg = entity.get("elemental_dmg", {})
    best_el = None
    best_val = 1.1
    for el, val in e_dmg.items():
        if val > best_val:
            best_val = val
            best_el = el
    if best_el:
        statuses.append(f"{best_el[:3].upper()}")

    return f" [{' '.join(statuses)}]" if statuses else ""


def _wrap_menu_lines(menu_str, max_width=66):
    """Split menu string into lines that fit within max_width."""
    if len(menu_str) <= max_width:
        return [menu_str]
    parts = menu_str.split('  ')
    lines = []
    current = ""
    for part in parts:
        if not current:
            current = part
        elif len(current) + 2 + len(part) <= max_width:
            current += "  " + part
        else:
            lines.append(current)
            current = part
    if current:
        lines.append(current)
    return lines


def print_combat_hud(player, enemies, active_ally=None, header=""):
    """Print the main combat HUD with a perfectly aligned party vs enemies layout."""
    allies = player.get("allies", [])  # Show all allies including defeated in HUD

    # Determine header context
    if not header:
        if is_abyssal_tempo_active(player):
            header = ">> ABYSSAL TEMPO ACTIVE <<"

    # 1. Top Border (Total inner width = 68 characters)
    print("+" + "-" * 68 + "+")
    if header:
        print("|" + _center_text(header, 68) + "|")
        # Fixed: Match the 32 | 35 column layout split
        print("+" + "-" * 32 + "+" + "-" * 35 + "+")

    # 2. Column Headers
    left_header = " YOUR PARTY"
    right_header = " ENEMIES"
    # Fixed: Padded smoothly to maintain strict 32 and 35 character column boundaries
    print(f"| {left_header:<30} | {right_header:<33} |")
    print(f"| {'-' * 30} | {'-' * 33} |")

    # 3. Gather Party Rows (2 rows per entity)
    party_rows = []
    _max_hp = 15 + player["attributes"]["Constitution"] * 3 + player.get("level_hp_bonus", 0)
    player_active = " >" if active_ally is None else ""

    # Player row 1: name + hp
    player_hp_str = f"{player['current_hp']}/{_max_hp}"
    party_rows.append(f"* You{player_active:<2} {player_hp_str:>12}")
    # Player row 2: buffs
    party_rows.append(_get_entity_buff_tags(player))

    for i, ally in enumerate(allies):
        is_active = (ally is active_ally)
        party_rows.append(format_ally_status_line(ally, idx=i+2, is_active=is_active))
        party_rows.append(_get_entity_buff_tags(ally))

    # 4. Gather Enemy Rows (2 rows per entity)
    enemy_rows = []
    for idx, e in enumerate(enemies):
        name = e['name'][:12]
        hp_str = f"{e['hp']}/{e['max_hp']}"
        mg_symbol = " ♀" if e.get("monster_girl") else ""
        enemy_rows.append(f"[{idx+1}] {name:<12} {hp_str:>8}{mg_symbol}")
        enemy_rows.append(_get_entity_buff_tags(e))

    # 5. Pad both sides to the same height
    max_rows = max(len(party_rows), len(enemy_rows), 4)
    while len(party_rows) < max_rows:
        party_rows.append("")
    while len(enemy_rows) < max_rows:
        enemy_rows.append("")

    # 6. Print Side-by-Side Content Columns
    # Fixed: Truncate and pad strings to fit perfectly into the 32 | 35 structure
    for pl, el in zip(party_rows, enemy_rows):
        safe_pl = pl[:30]
        safe_el = el[:33]
        print(f"| {safe_pl:<30} | {safe_el:<33} |")

    # 7. Bottom Frame Actions
    print("+" + "-" * 68 + "+")

    # Action menu
    if active_ally is not None:
        menu_str, _ = _ally_action_menu(active_ally, player, enemies)
    else:
        menu_str, _ = get_action_menu(player, enemies)
    for line in _wrap_menu_lines(menu_str):
        print(f"|  {line:<66}|")

    # Cooldown message (player only)
    if active_ally is None:
        cd_msg = get_abyss_fang_cooldown_display(player)
        if cd_msg:
            print(f"|  {cd_msg:<66}|")

        cd_msg2 = get_captain_cutlass_cooldown_display(player)
        if cd_msg2:
            print(f"|  {cd_msg2:<66}|")

        # Skill cooldown messages
        skill_cds = player.get('skill_cooldowns', {})
        if skill_cds:
            unlocked = get_all_unlocked_skills(player)
            for sid, sdef in unlocked:
                cd = skill_cds.get(sid, 0)
                if cd > 0:
                    cd_msg = f"({sdef['name']} recharging: {cd} turn(s))"
                    print(f"|  {cd_msg:<66}|")
    else:
        # Ally skill cooldown messages
        skill_cds = active_ally.get('skill_cooldowns', {})
        if skill_cds:
            all_skills = get_all_ally_skills(active_ally)
            for sid, sdef in all_skills:
                cd = skill_cds.get(sid, 0)
                if cd > 0:
                    cd_msg = f"({sdef['name']} recharging: {cd} turn(s))"
                    print(f"|  {cd_msg:<66}|")

    print("+" + "-" * 68 + "+")


def print_superboss_header(player, floor, boss_name, extra_gimmick_line=""):
    time_str = format_time(player.get("time_minutes", 0))
    if floor is not None:
        print(f" Floor {floor} - Superboss: {boss_name} | Time: {time_str}")
    else:
        print(f" Superboss: {boss_name} | Time: {time_str}")
    if extra_gimmick_line:
        print(extra_gimmick_line)
    status_line = format_player_status_line(player)
    tempo_str = " [Abyssal Tempo]" if is_abyssal_tempo_active(player) else ""
    print(f"\n{player['name']}: {player['current_hp']} {status_line}{tempo_str}".rstrip())


def print_player_mini_hud(player, enemies):
    """Inline HUD used during player turn in superboss loop - uses central action menu."""
    print_combat_hud(player, enemies)


def print_turn_order(turn_order, current_idx=None):
    """Print a compact turn order bar."""
    entries = []
    for i, c in enumerate(turn_order):
        marker = ">" if i == current_idx else " "
        label = c.get("label", "?")
        entries.append(f"{marker}{label}")
    print(f"  Turn Order: {' -> '.join(entries)}")


def print_round_header(round_num, floor=None, room_num=None, total_rooms=None, time_str=None):
    """Print a clean round header."""
    parts = [f">> ROUND {round_num}"]
    if floor is not None and room_num is not None and total_rooms is not None:
        parts.append(f"Floor {floor} | Room {room_num}/{total_rooms}")
    if time_str:
        parts.append(f"Time: {time_str}")
    print("  " + " | ".join(parts))
    print("  " + "-" * 66)
