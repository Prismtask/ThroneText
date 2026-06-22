# combat_ui.py – HUD and status formatting
from utils import clear_screen, format_time
from combat.status_effects import format_player_status_line
from combat.action_menu import get_action_menu
from combat.helpers import _player_has_abyss_fang
from combat.ally import get_alive_allies, format_ally_status_line


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


def print_combat_hud(player, enemies, active_ally=None):
    """Print the main combat HUD with a perfectly aligned party vs enemies layout."""
    allies = get_alive_allies(player)
    
    # Grid Dimensions (Total inner width = 68 characters)
    LEFT_COL_WIDTH = 31
    RIGHT_COL_WIDTH = 33
    # 31 (Left) + 4 (Middle separator " | ") + 33 (Right) = 68

    # Determine header context
    header = ""
    if player.get("abyss_triple_actions", 0) > 0:
        header = ">> ABYSSAL TEMPO ACTIVE <<"

    # 1. Top Border
    print("+" + "-" * 68 + "+")
    if header:
        print("|" + _center_text(header, 68) + "|")
        print("+" + "-" * LEFT_COL_WIDTH + "+" + "-" * (RIGHT_COL_WIDTH + 2) + "+")

    # 2. Column Headers
    left_header = f" YOUR PARTY"
    right_header = f" ENEMIES"
    print(f"| {left_header:<{LEFT_COL_WIDTH}}| {right_header:<{RIGHT_COL_WIDTH}} |")
    print(f"| " + "-" * (LEFT_COL_WIDTH - 1) + "| " + "-" * (RIGHT_COL_WIDTH) + "|")

    # 3. Gather Party Lines
    party_lines = []
    _max_hp = 15 + player["attributes"]["Constitution"] * 3 + player.get("level_hp_bonus", 0)
    player_active = " >" if active_ally is None else ""
    
    # Clean Player Status Formatting
    player_hp_str = f"{player['current_hp']}/{_max_hp}"
    party_lines.append(f"* You{player_active:<2} {player_hp_str:>12}")

    for i, ally in enumerate(allies):
        is_active = (ally is active_ally)
        # Note: Ensure format_ally_status_line doesn't exceed LEFT_COL_WIDTH - 2
        party_lines.append(format_ally_status_line(ally, idx=i+2, is_active=is_active))

    while len(party_lines) < 5:  # Match standard enemy padding heights
        party_lines.append("")

    # 4. Gather Enemy Lines
    enemy_lines = []
    for idx, e in enumerate(enemies):
        statuses = []
        for cond, tag in [("stunned", "STN"), ("slowed", "SLW"), ("blinded", "BLD"), ("frozen", "FRZ")]:
            if e.get(cond): statuses.append(tag)
        if any(d["type"] == "burn" for d in e.get("active_debuffs", [])):
            statuses.append("BRN")
            
        status_str_en = f" [{' '.join(statuses)}]" if statuses else ""
        name = e['name'][:12]  # Slightly truncated to guarantee safety margin
        hp_str = f"{e['hp']}/{e['max_hp']}"
        mg_symbol = " ♀" if e.get("monster_girl") else ""
        
        enemy_lines.append(f"[{idx+1}] {name:<12} {hp_str:>8}{status_str_en}{mg_symbol}")

    while len(enemy_lines) < 5:
        enemy_lines.append("")

    # 5. Print Side-by-Side Content Columns safely
    for pl, el in zip(party_lines, enemy_lines):
        # Truncate string pieces if they somehow overflow internal boundaries
        safe_pl = pl[:LEFT_COL_WIDTH - 1]
        safe_el = el[:RIGHT_COL_WIDTH]
        print(f"| {safe_pl:<{LEFT_COL_WIDTH-1}}| {safe_el:<{RIGHT_COL_WIDTH}} |")

    # 6. Bottom Frame Actions
    print("+" + "-" * 68 + "+")

    # Action menu
    menu_str, _ = get_action_menu(player, enemies)
    safe_menu = menu_str[:66]
    print(f"|  {safe_menu:<66}|")

    # Cooldown message
    if _player_has_abyss_fang(player) and player.get('abyss_fang_cooldown', 0) > 0:
        cd_msg = f"(Abyss Fang recharging: {player['abyss_fang_cooldown']} turn(s))"
        print(f"|  {cd_msg:<66}|")

    print("+" + "-" * 68 + "+")


def print_superboss_header(player, floor, boss_name, extra_gimmick_line=""):
    time_str = format_time(player.get("time_minutes", 0))
    print(f" {floor} - Superboss: {boss_name} | Time: {time_str}")
    if extra_gimmick_line:
        print(extra_gimmick_line)
    status_line = format_player_status_line(player)
    tempo_str = " [Abyssal Tempo]" if player.get("abyss_triple_actions", 0) > 0 else ""
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
