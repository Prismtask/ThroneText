# combat_ui.py – HUD and status formatting
from utils import clear_screen, format_time
from combat.status_effects import format_player_status_line
from combat.action_menu import get_action_menu
from combat.helpers import _player_has_abyss_fang        # <-- import from helpers


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

def print_combat_hud(player, enemies):
    """Print player status, enemy list, and action menu in one clean block."""
    status_str = format_player_status_line(player)
    tempo_str = " [Abyssal Tempo]" if player.get("abyss_triple_actions", 0) > 0 else ""
    print(f"\n{player['name']}: {player['current_hp']} {status_str}{tempo_str}".rstrip())

    print("Enemies in the room:")
    for idx, e in enumerate(enemies):
        print(f"  [{idx + 1}] {format_enemy_status_line(e)}")

    menu_str, _ = get_action_menu(player, enemies)
    print(menu_str)

    # Show cooldown message separately (non‑interactive)
    if _player_has_abyss_fang(player) and player.get('abyss_fang_cooldown', 0) > 0:
        print(f"(Abyss Fang recharging: {player['abyss_fang_cooldown']} turn(s))")

def print_superboss_header(player, floor, boss_name, extra_gimmick_line=""):
    time_str = format_time(player.get("time_minutes", 0))
    print(f" {floor} - Superboss: {boss_name} | Time: {time_str}")
    if extra_gimmick_line:
        print(extra_gimmick_line)
    status_line = format_player_status_line(player)
    tempo_str = " [Abyssal Tempo]" if player.get("abyss_triple_actions", 0) > 0 else ""
    print(f"\n{player['name']}: {player['current_hp']} {status_line}{tempo_str}".rstrip())


def print_player_mini_hud(player, enemies):
    """Inline HUD used during player turn in superboss loop – uses central action menu."""
    status_str = format_player_status_line(player)
    tempo_str = " [Abyssal Tempo]" if player.get("abyss_triple_actions", 0) > 0 else ""
    print(f"\n{player['name']}: {player['current_hp']} {status_str}{tempo_str}".rstrip())
    print("Enemies:")
    for idx, e in enumerate(enemies):
        print(f"  [{idx + 1}] {format_enemy_status_line(e)}")

    # Use the centralised menu generator
    menu_str, _ = get_action_menu(player, enemies)
    print(menu_str)

    # Show cooldown if applicable
    if _player_has_abyss_fang(player) and player.get('abyss_fang_cooldown', 0) > 0:
        print(f"(Abyss Fang recharging: {player['abyss_fang_cooldown']} turn(s))")