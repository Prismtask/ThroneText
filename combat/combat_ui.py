# combat_ui.py – HUD and status formatting
from utils import clear_screen, format_time
from combat.status_effects import format_player_status_line

def _player_has_abyss_fang(player):
    equipment = player.get("equipped", {})
    if isinstance(equipment, dict):
        weapon = equipment.get("weapon")
        if weapon and weapon.get("special") == "dream_devour":
            return weapon
    return None

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


def print_superboss_header(player, floor, boss_name, extra_gimmick_line=""):
    time_str = format_time(player.get("time_minutes", 0))
    print(f"Dungeon Floor {floor} - Superboss: {boss_name} | Time: {time_str}")
    if extra_gimmick_line:
        print(extra_gimmick_line)
    status_line = format_player_status_line(player)
    tempo_str = " [Abyssal Tempo]" if player.get("abyss_triple_actions", 0) > 0 else ""
    print(f"\n{player['name']}: {player['current_hp']} {status_line}{tempo_str}".rstrip())


def print_player_mini_hud(player, enemies):
    """Inline HUD used during player turn in superboss loop."""
    status_str = format_player_status_line(player)
    tempo_str = " [Abyssal Tempo]" if player.get("abyss_triple_actions", 0) > 0 else ""
    print(f"\n{player['name']}: {player['current_hp']} {status_str}{tempo_str}".rstrip())
    print("Enemies:")
    for idx, e in enumerate(enemies):
        print(f"  [{idx + 1}] {format_enemy_status_line(e)}")

    # --- Abyss Fang prompt logic (mirrors normal combat) ---
    abyss_fang = _player_has_abyss_fang(player)
    abyss_cd = player.get("abyss_fang_cooldown", 0)
    if abyss_fang and abyss_cd <= 0:
        print("[A]ttack  [D]efend  [F]lee  [U]se item  [W]ield the Abyss")
    elif abyss_fang and abyss_cd > 0:
        print(f"[A]ttack  [D]efend  [F]lee  [U]se item  (Abyss Fang recharging: {abyss_cd} turn(s))")
    else:
        print("[A]ttack  [D]efend  [F]lee  [U]se item")